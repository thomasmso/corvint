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
    NSLog(@"Interstitial failed to load: %@", error.message);
}

- (void)didDisplayAd:(MAAd *)ad {}

- (void)didClickAd:(MAAd *)ad {}

- (void)didHideAd:(MAAd *)ad
{
    [self.interstitialAd loadAd];
}

- (void)didFailToDisplayAd:(MAAd *)ad withError:(MAError *)error
{
    [self.interstitialAd loadAd];
}

@end
