#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Hints the player can spend on a puzzle.
@interface PQHintsStore : NSObject

@property (nonatomic, assign) NSInteger remaining;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
