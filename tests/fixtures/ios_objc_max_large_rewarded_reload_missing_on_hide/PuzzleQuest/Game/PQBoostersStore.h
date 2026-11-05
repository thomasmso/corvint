#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Boosters the player owns.
@interface PQBoostersStore : NSObject

@property (nonatomic, assign) NSInteger owned;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
