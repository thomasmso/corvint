#import "PQLeaderboardStore.h"

static NSString *const kKey = @"puzzlequest.leaderboard";

@implementation PQLeaderboardStore

+ (instancetype)sharedStore
{
    static PQLeaderboardStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQLeaderboardStore alloc] init];
    });
    return shared;
}

- (NSInteger)bestScore
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setBestScore:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
