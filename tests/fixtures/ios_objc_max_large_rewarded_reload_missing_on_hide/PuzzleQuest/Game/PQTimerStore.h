#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Fastest level completion, in seconds.
@interface PQTimerStore : NSObject

@property (nonatomic, assign) NSInteger bestSeconds;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
