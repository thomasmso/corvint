#import "AppDelegate.h"
#import "AdManager.h"
#import "GameViewController.h"

@implementation AppDelegate

- (BOOL)application:(UIApplication *)application didFinishLaunchingWithOptions:(NSDictionary *)launchOptions
{
    [[AdManager sharedManager] initializeSdk];

    self.window = [[UIWindow alloc] initWithFrame:[UIScreen mainScreen].bounds];
    self.window.rootViewController = [[GameViewController alloc] init];
    [self.window makeKeyAndVisible];
    return YES;
}

@end
