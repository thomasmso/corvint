#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Longest combo the player has made.
@interface PQComboStore : NSObject

@property (nonatomic, assign) NSInteger best;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
