#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Reward chests not opened yet.
@interface PQChestsStore : NSObject

@property (nonatomic, assign) NSInteger unopened;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
