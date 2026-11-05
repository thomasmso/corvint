#import <Foundation/Foundation.h>

@class InterstitialAdController;
@class RewardedAdController;

NS_ASSUME_NONNULL_BEGIN

@interface AdManager : NSObject

@property (nonatomic, strong, readonly, nullable) InterstitialAdController *interstitial;
@property (nonatomic, strong, readonly, nullable) RewardedAdController *rewarded;

+ (instancetype)sharedManager;
- (void)initializeSdk;
/// Runs `handler` once the SDK is initialized (immediately if it already is).
- (void)whenReady:(dispatch_block_t)handler;

@end

NS_ASSUME_NONNULL_END
