#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Live events the player has joined.
@interface PQEventsStore : NSObject

@property (nonatomic, assign) NSInteger activeCount;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
