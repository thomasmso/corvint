#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

/// Quests completed this season.
@interface PQQuestsStore : NSObject

@property (nonatomic, assign) NSInteger completed;

+ (instancetype)sharedStore;
- (void)reset;

@end

NS_ASSUME_NONNULL_END
