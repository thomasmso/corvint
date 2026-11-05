#import "GameViewController.h"

@interface GameViewController ()
@property (nonatomic, strong) UIButton *playButton;
@property (nonatomic, assign) NSInteger level;
@end

@implementation GameViewController

- (void)viewDidLoad
{
    [super viewDidLoad];
    self.view.backgroundColor = [UIColor systemBackgroundColor];
    self.level = 1;

    self.playButton = [UIButton buttonWithType:UIButtonTypeSystem];
    [self.playButton setTitle:@"Play" forState:UIControlStateNormal];
    [self.playButton addTarget:self action:@selector(playTapped) forControlEvents:UIControlEventTouchUpInside];
    self.playButton.translatesAutoresizingMaskIntoConstraints = NO;
    [self.view addSubview:self.playButton];
    [NSLayoutConstraint activateConstraints:@[
        [self.playButton.centerXAnchor constraintEqualToAnchor:self.view.centerXAnchor],
        [self.playButton.centerYAnchor constraintEqualToAnchor:self.view.centerYAnchor],
    ]];
}

- (void)playTapped
{
    // Gameplay is out of scope for this fixture; finishing a level is simulated.
    self.level += 1;
}

@end
