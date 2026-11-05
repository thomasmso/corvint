#import "PQSeasonPassStore.h"

static NSString *const kKey = @"puzzlequest.season_pass";

@implementation PQSeasonPassStore

+ (instancetype)sharedStore
{
    static PQSeasonPassStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQSeasonPassStore alloc] init];
    });
    return shared;
}

- (NSInteger)tier
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setTier:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
