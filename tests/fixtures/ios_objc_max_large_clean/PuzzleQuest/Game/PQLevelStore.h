#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Highest level the player has unlocked.
@interface PQLevelStore : NSObject

@property (nonatomic, assign) NSInteger current;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
