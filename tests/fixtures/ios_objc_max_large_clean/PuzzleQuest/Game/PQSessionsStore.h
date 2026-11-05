#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Number of app sessions.
@interface PQSessionsStore : NSObject

@property (nonatomic, assign) NSInteger count;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
