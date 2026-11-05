#import "PQAchievementsStore.h"

static NSString *const kKey = @"puzzlequest.achievements";

@implementation PQAchievementsStore

+ (instancetype)sharedStore
{
    static PQAchievementsStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQAchievementsStore alloc] init];
    });
    return shared;
}

- (NSInteger)unlockedCount
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setUnlockedCount:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
