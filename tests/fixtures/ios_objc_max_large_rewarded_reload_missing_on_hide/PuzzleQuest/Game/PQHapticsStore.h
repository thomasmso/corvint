#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Haptic feedback intensity, 0 to 3.
@interface PQHapticsStore : NSObject

@property (nonatomic, assign) NSInteger intensity;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
