"""
`adtech` command line: `chat` with the agent, `audit` one repository, `eval` the fixture suite, or
`install` pods through a pull request.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from collections.abc import Sequence
from pathlib import Path

import openai
from agents import AgentsException
from agents import _debug as agents_debug
from dotenv import find_dotenv, load_dotenv

from adtech_agents.chat_session import ChatSession
from adtech_agents.config import Config
from adtech_agents.context import Context
from adtech_agents.evals import render_scores, run_suite, save_results
from adtech_agents.github_app import GitHubError
from adtech_agents.project_changes import ChangeError
from adtech_agents.reference_data import ADAPTER_PODS, ReferenceDataError
from adtech_agents.tools.inspect_app_project import SDK_POD, UnsupportedProjectError
from adtech_agents.workflows.audit_max_integration_workflow import audit_max_integration
from adtech_agents.workflows.install_pods_workflow import install_pods
from adtech_agents.workspace import WorkspaceError


def main(argv: Sequence[str] | None = None) -> int:
    # Load .env file
    load_dotenv(find_dotenv(usecwd=True))
    args = build_parser().parse_args(argv)
    config = Config()

    # The chat shows its own progress lines; per-request logs would bury the conversation
    quiet = args.command == "chat" and not args.verbose
    logging.basicConfig(
        level=logging.WARNING if quiet else config.LOG_LEVEL, format=config.LOG_FORMAT
    )
    if config.LOG_AGENT_DATA:
        agents_debug.DONT_LOG_MODEL_DATA = False
        agents_debug.DONT_LOG_TOOL_DATA = False
        logging.getLogger("openai.agents").setLevel(logging.DEBUG)

    logging.info(f"Starting {args.command}: args={vars(args)} config={config}")

    # TODO: Integrate OpenRouter
    if args.command in ("audit", "eval", "chat") and not config.OPENAI_API_KEY:
        logging.error("OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.")
        return 2

    ctx = Context.create(config)
    try:
        return _run(args, ctx)
    finally:
        ctx.shutdown()


def _run(args: argparse.Namespace, ctx: Context) -> int:
    match args.command:
        case "chat":
            asyncio.run(_chat(ctx))
            return 0
        case "audit":
            try:
                report = asyncio.run(audit_max_integration(args.repo, ctx))
            except (UnsupportedProjectError, ReferenceDataError) as exc:
                logging.error(f"Cannot audit: {exc}")
                return 1
            print(report.model_dump_json(indent=2))
            return 0
        case "eval":
            scores = asyncio.run(run_suite(ctx))
            print(render_scores(scores))
            path = save_results(scores, ctx.config.EVAL_RESULTS_DIR)
            logging.info(f"Saved eval results to {path}")
            return 1 if any(score.error for score in scores) else 0
        # If want to test manually install pods (debugging shortcut essentially)
        case "install":
            try:
                result = install_pods(
                    args.repo, args.pod, ctx, on_step=lambda step: logging.info(f"Step: {step}")
                )
            except (ReferenceDataError, GitHubError, WorkspaceError, ChangeError) as exc:
                logging.error(f"Cannot install: {exc}")
                return 1
            if result.pull_request_url is None:
                print("Nothing to change: every pod already allows its newest version.")
            else:
                print(result.diff)
                if result.build is not None:
                    print(result.build.summary)
                    if result.build.log_tail:
                        print(result.build.log_tail)
                kind = "a draft pull request" if result.draft else "a pull request"
                print(f"Opened {kind}: {result.pull_request_url}")
            return 0
        case _:
            logging.error(f"Unknown command: {args.command}")
            return 2


async def _chat(ctx: Context) -> None:
    async def show_progress(line: str) -> None:
        print(f"\n{line}", flush=True)

    session = ChatSession(ctx, allow_local_paths=True, on_progress=show_progress)
    print(f"{session.text.greeting}\n{session.text.terminal_quit_hint}")
    while True:
        try:
            message = (await asyncio.to_thread(input, "\n> ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if message.lower() in ("exit", "quit"):
            return
        if not message:
            continue
        try:
            reply = await session.send(message)
        except (AgentsException, openai.APIError) as exc:
            logging.error(f"The agent failed: {exc}")
            continue
        print(f"\n{reply}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="command", required=True)

    chat = subparser.add_parser(
        "chat", help="Talk with the agent: audit a project, then open a pull request with pods."
    )
    chat.add_argument(
        "--verbose", action="store_true", help="Also log HTTP requests and every agent step."
    )

    audit = subparser.add_parser("audit", help="Audit one repository; prints the report as JSON.")
    audit.add_argument("--repo", type=Path, required=True)

    subparser.add_parser("eval", help="Run every fixture eval case (calls the model).")

    install = subparser.add_parser(
        "install", help="Install or update pods and open a pull request (GitHub App, see README)."
    )
    install.add_argument("--repo", required=True, help="Local git repository or GitHub URL.")
    install.add_argument(
        "--pod", action="append", required=True, choices=[SDK_POD, *ADAPTER_PODS.values()]
    )

    return parser


if __name__ == "__main__":
    raise SystemExit(main())
