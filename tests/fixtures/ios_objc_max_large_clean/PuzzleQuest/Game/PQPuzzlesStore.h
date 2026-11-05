#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Puzzles solved across all modes.
@interface PQPuzzlesStore : NSObject

@property (nonatomic, assign) NSInteger solved;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
