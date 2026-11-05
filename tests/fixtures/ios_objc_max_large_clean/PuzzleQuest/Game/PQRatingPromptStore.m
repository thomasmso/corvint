#import "PQRatingPromptStore.h"

static NSString *const kKey = @"puzzlequest.rating_prompt";

@implementation PQRatingPromptStore

+ (instancetype)sharedStore
{
    static PQRatingPromptStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQRatingPromptStore alloc] init];
    });
    return shared;
}

- (NSInteger)timesShown
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setTimesShown:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
