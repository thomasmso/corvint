#import "PQSessionsStore.h"

static NSString *const kKey = @"puzzlequest.sessions";

@implementation PQSessionsStore

+ (instancetype)sharedStore
{
    static PQSessionsStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQSessionsStore alloc] init];
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
