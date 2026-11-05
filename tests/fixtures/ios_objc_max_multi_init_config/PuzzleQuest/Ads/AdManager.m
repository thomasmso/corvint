#import "AdManager.h"
#import <AppLovinSDK/AppLovinSDK.h>
#import "InterstitialAdController.h"
#import "RewardedAdController.h"

// TODO: add the SDK key before release
static NSString *const kSdkKey = @"";

@interface AdManager ()
@property (nonatomic, strong, readwrite, nullable) InterstitialAdController *interstitial;
@property (nonatomic, strong, readwrite, nullable) RewardedAdController *rewarded;
@property (nonatomic, assign) BOOL initialized;
@property (nonatomic, strong) NSMutableArray<dispatch_block_t> *readyHandlers;
@end

@implementation AdManager

+ (instancetype)sharedManager
{
    static AdManager *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[AdManager alloc] init];
    });
    return shared;
}

- (instancetype)init
{
    self = [super init];
    if ( self )
    {
        _readyHandlers = [NSMutableArray array];
    }
    return self;
}

- (void)initializeSdk
{
    ALSdkInitializationConfiguration *initConfig = [ALSdkInitializationConfiguration configurationWithSdkKey:kSdkKey builderBlock:^(ALSdkInitializationConfigurationBuilder *builder) {
        builder.testDeviceAdvertisingIdentifiers = @[];
    }];

    [[ALSdk shared] initializeWithConfiguration:initConfig completionHandler:^(ALSdkConfiguration *sdkConfig) {
        self.initialized = YES;

        self.interstitial = [[InterstitialAdController alloc] initWithAdUnitIdentifier:@"c4f7e9a1b2d30658"];
        [self.interstitial load];

        self.rewarded = [[RewardedAdController alloc] initWithAdUnitIdentifier:@"9e2b6d4f1a7c8035"];
        [self.rewarded load];

        for ( dispatch_block_t handler in self.readyHandlers )
        {
            handler();
        }
        [self.readyHandlers removeAllObjects];
    }];
}

- (void)whenReady:(dispatch_block_t)handler
{
    if ( self.initialized )
    {
        handler();
    }
    else
    {
        [self.readyHandlers addObject:handler];
    }
}

@end
