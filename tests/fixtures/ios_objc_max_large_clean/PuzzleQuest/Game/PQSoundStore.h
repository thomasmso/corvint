#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Sound effects volume, 0 to 100.
@interface PQSoundStore : NSObject

@property (nonatomic, assign) NSInteger volume;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
