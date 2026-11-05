#import "AppBootstrap.h"
#import "AdManager.h"

@implementation AppBootstrap

+ (void)startWithLaunchOptions:(NSDictionary *)launchOptions
{
    [self registerDefaults];
    [[AdManager sharedManager] initializeSdk];
}

+ (void)registerDefaults
{
    [[NSUserDefaults standardUserDefaults] registerDefaults:@{
        @"puzzlequest.soundEnabled": @YES,
        @"puzzlequest.hapticsEnabled": @YES,
    }];
}

@end
