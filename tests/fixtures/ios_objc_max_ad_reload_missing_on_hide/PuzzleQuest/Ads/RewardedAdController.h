#import <Foundation/Foundation.h>

@class MAReward;

NS_ASSUME_NONNULL_BEGIN

@interface RewardedAdController : NSObject

- (instancetype)initWithAdUnitIdentifier:(NSString *)adUnitIdentifier;
- (void)load;
- (void)showIfReadyWithReward:(void (^)(MAReward *reward))onReward;

@end

NS_ASSUME_NONNULL_END
