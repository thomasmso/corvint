#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Consecutive days the player has opened the game.
@interface PQStreakStore : NSObject

@property (nonatomic, assign) NSInteger days;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
