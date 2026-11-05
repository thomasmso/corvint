#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Tile skins unlocked.
@interface PQSkinsStore : NSObject

@property (nonatomic, assign) NSInteger unlocked;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
