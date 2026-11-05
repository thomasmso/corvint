#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Best score submitted to the leaderboard.
@interface PQLeaderboardStore : NSObject

@property (nonatomic, assign) NSInteger bestScore;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
