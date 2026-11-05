#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// App icon badge count for unread notifications.
@interface PQBadgesStore : NSObject

@property (nonatomic, assign) NSInteger count;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
