#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Gifts from friends waiting to be opened.
@interface PQGiftsStore : NSObject

@property (nonatomic, assign) NSInteger pending;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
