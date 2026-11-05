#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Tiles cleared in total.
@interface PQTilesStore : NSObject

@property (nonatomic, assign) NSInteger cleared;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
