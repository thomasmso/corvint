#import "PQStreakStore.h"

static NSString *const kKey = @"puzzlequest.streak";

@implementation PQStreakStore

+ (instancetype)sharedStore
{
    static PQStreakStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQStreakStore alloc] init];
    });
    return shared;
}

- (NSInteger)days
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setDays:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
