#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Number of achievements unlocked.
@interface PQAchievementsStore : NSObject

@property (nonatomic, assign) NSInteger unlockedCount;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
