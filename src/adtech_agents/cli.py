"""
`adtech` command line: `audit` one repository or `eval` the fixture suite.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from collections.abc import Sequence
from pathlib import Path

from agents import _debug as agents_debug
from dotenv import find_dotenv, load_dotenv

from adtech_agents.config import Config
from adtech_agents.context import Context
from adtech_agents.evals import render_scores, run_suite, save_results
from adtech_agents.reference_data import ReferenceDataError
from adtech_agents.tools.inspect_app_project import UnsupportedProjectError
from adtech_agents.workflows.audit_max_integration_workflow import audit_max_integration


#
# TODO: GitHub connector that can be triggered via webapp to audit or install new adapters.
#
def main(argv: Sequence[str] | None = None) -> int:
    # Load .env file
    load_dotenv(find_dotenv(usecwd=True))
    args = build_parser().parse_args(argv)
    config = Config()

    logging.basicConfig(level=config.LOG_LEVEL, format=config.LOG_FORMAT)
    if config.LOG_AGENT_DATA:
        agents_debug.DONT_LOG_MODEL_DATA = False
        agents_debug.DONT_LOG_TOOL_DATA = False
        logging.getLogger("openai.agents").setLevel(logging.DEBUG)

    logging.info(f"Starting {args.command}: args={vars(args)} config={config}")

    # TODO: Integrate OpenRouter
    if not config.OPENAI_API_KEY:
        logging.error("OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.")
        return 2

    ctx = Context.create(config)
    try:
        return _run(args, ctx)
    finally:
        ctx.shutdown()


def _run(args: argparse.Namespace, ctx: Context) -> int:
    # TODO: Implement chat mode (then we'd need `ask_user` tool, et al)
    match args.command:
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
        case _:
            logging.error(f"Unknown command: {args.command}")
            return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="command", required=True)

    audit = subparser.add_parser("audit", help="Audit one repository; prints the report as JSON.")
    audit.add_argument("--repo", type=Path, required=True)

    subparser.add_parser("eval", help="Run every fixture eval case (calls the model).")

    return parser


if __name__ == "__main__":
    raise SystemExit(main())
