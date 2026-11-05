#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Furthest tutorial step the player has seen.
@interface PQTutorialStore : NSObject

@property (nonatomic, assign) NSInteger step;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
