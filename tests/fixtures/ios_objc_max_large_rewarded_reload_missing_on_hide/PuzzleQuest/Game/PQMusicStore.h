#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Music volume, 0 to 100.
@interface PQMusicStore : NSObject

@property (nonatomic, assign) NSInteger volume;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
