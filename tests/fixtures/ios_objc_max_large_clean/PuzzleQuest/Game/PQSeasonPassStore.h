#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Current season pass tier.
@interface PQSeasonPassStore : NSObject

@property (nonatomic, assign) NSInteger tier;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
