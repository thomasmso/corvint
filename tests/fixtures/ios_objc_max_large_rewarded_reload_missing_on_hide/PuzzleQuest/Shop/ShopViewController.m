#import "ShopViewController.h"
#import "AdManager.h"
#import "PQCoinsStore.h"
#import "RewardedAdController.h"

@interface ShopViewController ()
@property (nonatomic, strong) UIButton *watchAdButton;
@end

@implementation ShopViewController

- (void)viewDidLoad
{
    [super viewDidLoad];
    self.view.backgroundColor = [UIColor systemBackgroundColor];

    self.watchAdButton = [UIButton buttonWithType:UIButtonTypeSystem];
    [self.watchAdButton setTitle:@"Watch an ad for 50 coins" forState:UIControlStateNormal];
    [self.watchAdButton addTarget:self action:@selector(watchAdTapped) forControlEvents:UIControlEventTouchUpInside];
    self.watchAdButton.translatesAutoresizingMaskIntoConstraints = NO;
    [self.view addSubview:self.watchAdButton];
    [NSLayoutConstraint activateConstraints:@[
        [self.watchAdButton.centerXAnchor constraintEqualToAnchor:self.view.centerXAnchor],
        [self.watchAdButton.centerYAnchor constraintEqualToAnchor:self.view.centerYAnchor],
    ]];
}

- (void)watchAdTapped
{
    [[AdManager sharedManager].rewarded showIfReadyWithReward:^(MAReward *reward) {
        [PQCoinsStore sharedStore].balance += 50;
    }];
}

@end
