#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Index of the selected board theme.
@interface PQThemeStore : NSObject

@property (nonatomic, assign) NSInteger selectedIndex;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
