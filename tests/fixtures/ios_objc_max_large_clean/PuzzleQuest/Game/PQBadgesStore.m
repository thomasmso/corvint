#import "PQBadgesStore.h"

static NSString *const kKey = @"puzzlequest.badges";

@implementation PQBadgesStore

+ (instancetype)sharedStore
{
    static PQBadgesStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQBadgesStore alloc] init];
    });
    return shared;
}

- (NSInteger)count
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setCount:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
