#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

@interface InterstitialAdController : NSObject

- (instancetype)initWithAdUnitIdentifier:(NSString *)adUnitIdentifier;
- (void)load;
- (void)showIfReady;

@end

NS_ASSUME_NONNULL_END
