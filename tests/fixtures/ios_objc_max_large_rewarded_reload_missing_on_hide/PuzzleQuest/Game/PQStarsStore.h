#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Stars earned across all levels.
@interface PQStarsStore : NSObject

@property (nonatomic, assign) NSInteger total;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
