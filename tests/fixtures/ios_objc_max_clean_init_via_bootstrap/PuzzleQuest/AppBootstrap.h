#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Starts the app's services at launch.
@interface AppBootstrap : NSObject

+ (void)startWithLaunchOptions:(nullable NSDictionary *)launchOptions;

@end

NS_ASSUME_NONNULL_END
