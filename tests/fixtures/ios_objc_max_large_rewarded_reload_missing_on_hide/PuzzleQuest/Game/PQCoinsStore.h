#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Soft currency earned in levels and the shop.
@interface PQCoinsStore : NSObject

@property (nonatomic, assign) NSInteger balance;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
