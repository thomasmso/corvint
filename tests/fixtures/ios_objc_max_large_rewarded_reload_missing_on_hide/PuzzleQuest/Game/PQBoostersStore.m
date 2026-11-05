#import "PQBoostersStore.h"

static NSString *const kKey = @"puzzlequest.boosters";

@implementation PQBoostersStore

+ (instancetype)sharedStore
{
    static PQBoostersStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQBoostersStore alloc] init];
    });
    return shared;
}

- (NSInteger)owned
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setOwned:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
