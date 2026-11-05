#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Day number of the last claimed daily reward.
@interface PQDailyRewardStore : NSObject

@property (nonatomic, assign) NSInteger lastClaimDay;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
