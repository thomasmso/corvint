#import "InterstitialAdController.h"
#import <AppLovinSDK/AppLovinSDK.h>

@interface InterstitialAdController () <MAAdDelegate>
@property (nonatomic, strong) MAInterstitialAd *interstitialAd;
@property (nonatomic, assign) NSInteger retryAttempt;
@end

@implementation InterstitialAdController

- (instancetype)initWithAdUnitIdentifier:(NSString *)adUnitIdentifier
{
    self = [super init];
    if ( self )
    {
        _interstitialAd = [[MAInterstitialAd alloc] initWithAdUnitIdentifier:adUnitIdentifier];
        _interstitialAd.delegate = self;
    }
    return self;
}

- (void)load
{
    [self.interstitialAd loadAd];
}

- (void)showIfReady
{
    if ( [self.interstitialAd isReady] )
    {
        [self.interstitialAd showAd];
    }
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
        [weakSelf.interstitialAd loadAd];
    });
}

- (void)didDisplayAd:(MAAd *)ad {}

- (void)didClickAd:(MAAd *)ad {}

- (void)didHideAd:(MAAd *)ad
{
    [self.interstitialAd loadAd];
}

- (void)didFailToDisplayAd:(MAAd *)ad withError:(MAError *)error {}

@end
