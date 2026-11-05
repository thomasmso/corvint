#import "PQDailyRewardStore.h"

static NSString *const kKey = @"puzzlequest.daily_reward";

@implementation PQDailyRewardStore

+ (instancetype)sharedStore
{
    static PQDailyRewardStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQDailyRewardStore alloc] init];
    });
    return shared;
}

- (NSInteger)lastClaimDay
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setLastClaimDay:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
