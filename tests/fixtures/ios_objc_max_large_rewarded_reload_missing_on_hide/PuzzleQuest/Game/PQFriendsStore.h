#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Friends connected to the player's profile.
@interface PQFriendsStore : NSObject

@property (nonatomic, assign) NSInteger count;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
