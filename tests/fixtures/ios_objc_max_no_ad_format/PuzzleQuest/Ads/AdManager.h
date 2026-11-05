#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

@interface AdManager : NSObject

+ (instancetype)sharedManager;
- (void)initializeSdk;

@end

NS_ASSUME_NONNULL_END
