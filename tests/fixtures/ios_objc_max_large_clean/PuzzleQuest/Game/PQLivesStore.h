#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Lives left before the player must wait or refill.
@interface PQLivesStore : NSObject

@property (nonatomic, assign) NSInteger count;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
