#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Number of items in the player's inventory.
@interface PQInventoryStore : NSObject

@property (nonatomic, assign) NSInteger itemCount;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
