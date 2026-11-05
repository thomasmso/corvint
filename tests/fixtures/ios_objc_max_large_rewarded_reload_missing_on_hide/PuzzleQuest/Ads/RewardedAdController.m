#import "RewardedAdController.h"
#import <AppLovinSDK/AppLovinSDK.h>

@interface RewardedAdController () <MARewardedAdDelegate>
@property (nonatomic, strong) MARewardedAd *rewardedAd;
@property (nonatomic, assign) NSInteger retryAttempt;
@property (nonatomic, copy, nullable) void (^onReward)(MAReward *reward);
@end

@implementation RewardedAdController

- (instancetype)initWithAdUnitIdentifier:(NSString *)adUnitIdentifier
{
    self = [super init];
    if ( self )
    {
        _rewardedAd = [MARewardedAd sharedWithAdUnitIdentifier:adUnitIdentifier];
        _rewardedAd.delegate = self;
    }
    return self;
}

- (void)load
{
    [self.rewardedAd loadAd];
}

- (void)showIfReadyWithReward:(void (^)(MAReward *reward))onReward
{
    if ( ![self.rewardedAd isReady] )
    {
        return;
    }
    self.onReward = onReward;
    [self.rewardedAd showAd];
}

#pragma mark - MAAdDelegate

- (void)didLoadAd:(MAAd *)ad
{
    self.retryAttempt = 0;
}

- (void)didFailToLoadAdForAdUnitIdentifier:(NSString *)adUnitIdentifier withError:(MAError *)error
{
    // Retry with exponentially higher delays, up to 64 seconds
    self.retryAttempt++;
    NSInteger delaySec = pow(2, MIN(6, self.retryAttempt));
    __weak typeof(self) weakSelf = self;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW, delaySec * NSEC_PER_SEC), dispatch_get_main_queue(), ^{
        [weakSelf.rewardedAd loadAd];
    });
}

- (void)didDisplayAd:(MAAd *)ad {}

- (void)didClickAd:(MAAd *)ad {}

- (void)didHideAd:(MAAd *)ad {}

- (void)didFailToDisplayAd:(MAAd *)ad withError:(MAError *)error
{
    [self.rewardedAd loadAd];
}

#pragma mark - MARewardedAdDelegate

- (void)didRewardUserForAd:(MAAd *)ad withReward:(MAReward *)reward
{
    if ( self.onReward )
    {
        self.onReward(reward);
    }
    self.onReward = nil;
}

@end
