#import "GameViewController.h"
#import <AppLovinSDK/AppLovinSDK.h>
#import "AdManager.h"
#import "InterstitialAdController.h"
#import "RewardedAdController.h"

@interface GameViewController () <MAAdViewAdDelegate>
@property (nonatomic, strong) UIButton *playButton;
@property (nonatomic, strong) UIButton *hintButton;
@property (nonatomic, strong) MAAdView *bannerView;
@property (nonatomic, assign) NSInteger hints;
@property (nonatomic, assign) NSInteger level;
@end

@implementation GameViewController

- (void)viewDidLoad
{
    [super viewDidLoad];
    self.view.backgroundColor = [UIColor systemBackgroundColor];
    self.hints = 3;
    self.level = 1;

    self.playButton = [UIButton buttonWithType:UIButtonTypeSystem];
    [self.playButton setTitle:@"Play" forState:UIControlStateNormal];
    [self.playButton addTarget:self action:@selector(playTapped) forControlEvents:UIControlEventTouchUpInside];
    self.hintButton = [UIButton buttonWithType:UIButtonTypeSystem];
    [self.hintButton setTitle:@"Get a hint" forState:UIControlStateNormal];
    [self.hintButton addTarget:self action:@selector(hintTapped) forControlEvents:UIControlEventTouchUpInside];

    UIStackView *stack = [[UIStackView alloc] initWithArrangedSubviews:@[self.playButton, self.hintButton]];
    stack.axis = UILayoutConstraintAxisVertical;
    stack.spacing = 16;
    stack.translatesAutoresizingMaskIntoConstraints = NO;
    [self.view addSubview:stack];
    [NSLayoutConstraint activateConstraints:@[
        [stack.centerXAnchor constraintEqualToAnchor:self.view.centerXAnchor],
        [stack.centerYAnchor constraintEqualToAnchor:self.view.centerYAnchor],
    ]];

    __weak typeof(self) weakSelf = self;
    [[AdManager sharedManager] whenReady:^{
        [weakSelf attachBanner];
    }];
}

- (void)playTapped
{
    [[AdManager sharedManager] initializeSdk];
    [self startLevel];
}

- (void)hintTapped
{
    __weak typeof(self) weakSelf = self;
    [[AdManager sharedManager].rewarded showIfReadyWithReward:^(MAReward *reward) {
        weakSelf.hints += 1;
    }];
}

- (void)startLevel
{
    // Gameplay is out of scope for this fixture; finishing a level is simulated.
    [self levelCompleted];
}

- (void)levelCompleted
{
    self.level += 1;
    [[AdManager sharedManager].interstitial showIfReady];
}

- (void)attachBanner
{
    MAAdView *adView = [[MAAdView alloc] initWithAdUnitIdentifier:@"5a8c1e3f7b2d9046"];
    adView.delegate = self;
    adView.backgroundColor = [UIColor blackColor];
    adView.translatesAutoresizingMaskIntoConstraints = NO;
    [self.view addSubview:adView];

    CGFloat height = (UIDevice.currentDevice.userInterfaceIdiom == UIUserInterfaceIdiomPad) ? 90 : 50;
    [NSLayoutConstraint activateConstraints:@[
        [adView.leadingAnchor constraintEqualToAnchor:self.view.leadingAnchor],
        [adView.trailingAnchor constraintEqualToAnchor:self.view.trailingAnchor],
        [adView.bottomAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.bottomAnchor],
        [adView.heightAnchor constraintEqualToConstant:height],
    ]];

    [adView loadAd];
    self.bannerView = adView;
}

#pragma mark - MAAdViewAdDelegate (banners refresh automatically)

- (void)didLoadAd:(MAAd *)ad {}

- (void)didFailToLoadAdForAdUnitIdentifier:(NSString *)adUnitIdentifier withError:(MAError *)error {}

- (void)didClickAd:(MAAd *)ad {}

- (void)didFailToDisplayAd:(MAAd *)ad withError:(MAError *)error {}

- (void)didExpandAd:(MAAd *)ad {}

- (void)didCollapseAd:(MAAd *)ad {}

- (void)didDisplayAd:(MAAd *)ad {}

- (void)didHideAd:(MAAd *)ad {}

@end
