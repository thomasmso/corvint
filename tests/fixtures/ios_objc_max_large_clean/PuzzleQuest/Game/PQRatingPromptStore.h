#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Times the app rating prompt has been shown.
@interface PQRatingPromptStore : NSObject

@property (nonatomic, assign) NSInteger timesShown;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
